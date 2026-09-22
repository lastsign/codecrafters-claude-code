class Solution:
    def minFallingPathSum(self, matrix: list[list[int]]) -> int:
        m = len(matrix)
        n = len(matrix[0])
        dp = [[float("inf")] * (n + 1) for _ in range(m)]
        for col in range(n):
            dp[0][col] = matrix[0][col]
        for row in range(1, m):
            for col in range(n):
                dp[row][col] = matrix[row][col] + min(
                    dp[row - 1][col - 1], dp[row - 1][col], dp[row - 1][col + 1]
                )
        ans = float("inf")
        for col in range(n):
            ans = min(ans, dp[m - 1][col])
        return ans
