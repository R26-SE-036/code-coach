package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix022 {
    public int getRightEdge(int[][] grid) {
        return grid[0][grid[0].length - 1];
    }
}