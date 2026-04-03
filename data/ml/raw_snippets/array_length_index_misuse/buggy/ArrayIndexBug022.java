public class ArrayIndexBug022 {
    public int getRightEdge(int[][] grid) {
        return grid[0][grid[0].length];
    }
}