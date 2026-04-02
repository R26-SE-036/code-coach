public class OffByOneFix014 {
    public void iterateCols(int[][] matrix) {
        for (int c = 0; c < matrix[0].length; c++) {
            matrix[0][c] = 1;
        }
    }
}