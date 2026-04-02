public class OffByOneBug013 {
    public void iterateRows(int[][] matrix) {
        for (int r = 0; r <= matrix.length; r++) {
            matrix[r][0] = 1;
        }
    }
}