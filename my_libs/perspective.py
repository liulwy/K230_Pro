def _mat_mult(a, b):
    # 3x3矩阵与3x1向量相乘
    return [
        a[0][0]*b[0] + a[0][1]*b[1] + a[0][2]*b[2],
        a[1][0]*b[0] + a[1][1]*b[1] + a[1][2]*b[2],
        a[2][0]*b[0] + a[2][1]*b[1] + a[2][2]*b[2]
    ]

def _solve_linear_system(A, B):
    # 高斯消元法解线性方程组Ax=B
    n = len(B)
    for i in range(n):
        # 寻找主元
        max_row = i
        for j in range(i+1, n):
            if abs(A[j][i]) > abs(A[max_row][i]):
                max_row = j
        A[i], A[max_row] = A[max_row], A[i]
        B[i], B[max_row] = B[max_row], B[i]
        # 消元
        for j in range(i+1, n):
            if A[i][i] == 0:
                continue
            f = A[j][i] / A[i][i]
            for k in range(i, n):
                A[j][k] -= f * A[i][k]
            B[j] -= f * B[i]
    # 回代
    x = [0 for _ in range(n)]
    for i in range(n-1, -1, -1):
        x[i] = B[i]
        for j in range(i+1, n):
            x[i] -= A[i][j] * x[j]
        if A[i][i] == 0:
            x[i] = 0
        else:
            x[i] /= A[i][i]
    return x

def get_perspective_transform(src, dst):
    # src/dst: 4个点，每个点[x, y]
    A = []
    B = []
    for i in range(4):
        x, y = src[i]
        u, v = dst[i]
        A.append([x, y, 1, 0, 0, 0, -u*x, -u*y])
        B.append(u)
        A.append([0, 0, 0, x, y, 1, -v*x, -v*y])
        B.append(v)
    h = _solve_linear_system(A, B)
    h.append(1.0)
    # 3x3矩阵
    H = [
        [h[0], h[1], h[2]],
        [h[3], h[4], h[5]],
        [h[6], h[7], h[8]]
    ]
    return H

def mat_inv(m):
    # 3x3矩阵求逆，纯Python实现
    a,b,c = m[0]
    d,e,f = m[1]
    g,h,i = m[2]
    A = e*i-f*h
    B = c*h-b*i
    C = b*f-c*e
    D = f*g-d*i
    E = a*i-c*g
    F = c*d-a*f
    G = d*h-e*g
    H = b*g-a*h
    I = a*e-b*d
    det = a*A + b*D + c*G
    if det == 0:
        return m  # 不可逆，直接返回原矩阵
    inv = [
        [A/det, B/det, C/det],
        [D/det, E/det, F/det],
        [G/det, H/det, I/det]
    ]
    return inv

def perspective_transform_point(pt, H):
    x, y = pt
    vec = [x, y, 1.0]
    res = _mat_mult(H, vec)
    return (res[0]/res[2], res[1]/res[2])