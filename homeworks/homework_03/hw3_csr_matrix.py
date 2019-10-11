#!/usr/bin/env python
# coding: utf-8


import numpy as np


class CSRMatrix:
    """
    CSR (2D) matrix.
    Here you can read how CSR sparse matrix works: https://en.wikipedia.org/wiki/Sparse_matrix
    Must be implemented:
    1. Getting and setting element by indexes of row and col.
    a[i, j] = v -- set value in i-th row and j-th column to value
    b = a[i, j] -- get value from i-th row and j-th column
    2. Pointwise operations.
    c = a + b -- sum of two CSR matrix of the same shape
    c = a - b -- difference --//--
    c = a * b -- product --//--
    c = alpha * a -- product of scalar alpha and CSR matrix a
    c = a / alpha -- divide CSR matrix a by nonzero scalar alpha
    3. Scalar product
    c = a.dot(b) -- matrix multiplication if shapes match
    c = a @ b --//--
    4. nnz attribute -- number of nonzero elements in matrix
    """

    def __init__(self, init_matrix_representation):
        """
        :param init_matrix_representation: can be usual dense matrix
        or
        (row_ind, col, data) tuple with np.arrays,
            where data, row_ind and col_ind satisfy the relationship:
            a[row_ind[k], col_ind[k]] = data[k]
        """

        self._nnz = 0
        self.shape = []
        self.row_ind = []
        self.column_ind = []
        self.data = []

        if isinstance(init_matrix_representation, tuple) and len(init_matrix_representation) == 3:
            self.row_ind, self.column_ind, self.data = init_matrix_representation[0], init_matrix_representation[1], \
                                                       init_matrix_representation[2]

        elif isinstance(init_matrix_representation, np.ndarray):
            for i in range(init_matrix_representation.shape[0]):
                for j in range(init_matrix_representation.shape[1]):
                    if init_matrix_representation[i, j] != 0:
                        self.data.append(init_matrix_representation[i, j])
                        self.row_ind.append(i)
                        self.column_ind.append(j)
            self.shape = init_matrix_representation.shape
        else:
            raise ValueError
        self._nnz = len(self.data)

    nnz = property()

    @nnz.getter
    def nnz(self):
        return self._nnz

    def __getitem__(self, item):
        for i, j, data in zip(self.row_ind, self.column_ind, self.data):
            if item[0] == i and item[1] == j:
                return data
        return 0

    def __setitem__(self, key, value):
        for i, j, k in zip(self.row_ind, self.column_ind, range(len(self.data) + 1)):
            if key[0] == i and key[1] == j:
                if value == 0:
                    self.data.pop(k)
                    self.row_ind.pop(k)
                    self.column_ind.pop(k)
                    self._nnz -= 1
                else:
                    self.data[k] = value
                return
            elif key[0] == i and key[1] > j or key[0] > i:
                if k != len(self.data):
                    self.row_ind.insert(k, key[0])
                    self.column_ind.insert(k, key[1])
                    self.data.insert(k, value)
                self._nnz += 1
                return

        self.row_ind.append(key[0])
        self.column_ind.append(key[1])
        self.data.append(value)

    def __add__(self, other):
        return CSRMatrix(self._op(other, action='add'))

    def __sub__(self, other):
        return CSRMatrix(self._op(other, action='sub'))

    def __mul__(self, other):
        return CSRMatrix(self._op(other, action='mul'))

    def _op(self, other, action):
        i, j = 0, 0
        _len = len(self.row_ind)
        res_row, res_cl, res_data = [], [], []

        while i < _len:
            if j == len(other.data):
                if action != 'mul':
                    res_row += self.row_ind[i:]
                    res_cl += self.column_ind[i:]
                    res_data += self.data[i:]
                break
            if (other.row_ind[j] < self.row_ind[i]) or (other.row_ind[j] == self.row_ind[i] and
                                                        other.column_ind[j] < self.column_ind[i]):
                if action != 'mul':
                    res_row.append(other.row_ind[j])
                    res_cl.append(other.column_ind[j])
                if action == 'add':
                    res_data.append(other.data[j])
                elif action == 'sub':
                    res_data.append(-other.data[j])
                j += 1
            elif other.row_ind[j] == self.row_ind[i] and other.column_ind[j] == self.column_ind[i]:
                if action == 'add':
                    if other.data[j] + self.data[i] == 0:
                        i, j = i + 1, j + 1
                        continue
                    res_data.append(other.data[j] + self.data[i])
                elif action == 'sub':
                    if self.data[i] - other.data[j] == 0:
                        i, j = i + 1, j + 1
                        continue
                    res_data.append(self.data[i] - other.data[j])
                else:
                    res_data.append(other.data[j] * self.data[i])
                res_row.append(other.row_ind[j])
                res_cl.append(other.column_ind[j])
                i, j = i + 1, j + 1
            elif (other.row_ind[j] > self.row_ind[i]) or (other.row_ind[j] == self.row_ind[i] and
                                                          other.column_ind[j] > self.column_ind[i]):
                if action != 'mul':
                    res_row.append(self.row_ind[i])
                    res_cl.append(self.column_ind[i])
                    res_data.append(self.data[i])
                i += 1

        if j < len(other.data) and action != 'mul':
            res_row += other.row_ind[j:]
            res_cl += other.column_ind[j:]
            if action == 'add':
                res_data += other.data[j:]
            else:
                for i in other.data[j:]:
                    res_data.append(-i)
        return res_row, res_cl, res_data

    def __truediv__(self, other):
        if other == 0:
            return
        return CSRMatrix(tuple([self.row_ind, self.column_ind, [i / other for i in self.data]]))

    def __rmul__(self, other):
        if other == 0:
            return CSRMatrix(tuple([[], [], []]))
        return CSRMatrix(tuple([self.row_ind, self.column_ind, [i * other for i in self.data]]))

    def __matmul__(self, other):
        if self.shape[-1] != other.shape[0]:
            raise ValueError
        res = {}
        for row_1, column_1, data_1 in zip(self.row_ind, self.column_ind, self.data):
            for row_2, column_2, data_2 in zip(other.row_ind, other.column_ind, other.data):
                if column_1 != row_2:
                    continue
                if (row_1, column_2) in res:
                    res[(row_1, column_2)] += data_1 * data_2
                else:
                    res[(row_1, column_2)] = data_1 * data_2

        res_row, res_col, res_dat = [], [], []
        for item in res.items():
            if not item[1]:
                continue
            res_row.append(item[0][0])
            res_col.append(item[0][1])
            res_dat.append(item[1])

        return CSRMatrix(tuple([res_row, res_col, res_dat]))

    def to_dense(self):
        """
        Return dense representation of matrix (2D np.array).
        """

        dense_matrix = np.zeros((self.row_ind[-1] + 1, self.column_ind[-1] + 1))
        for i, j, data in zip(self.row_ind, self.column_ind, self.data):
            dense_matrix[i, j] = data
        return dense_matrix