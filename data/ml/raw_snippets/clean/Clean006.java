package data.ml.raw_snippets.clean;

public class Clean006 {
    public static void main(String[] args) {
        int[][] grid = {
                { 1, 2 },
                { 3, 4 }
        };

        for (int row = 0; row < grid.length; row++) {
            for (int col = 0; col < grid[row].length; col++) {
                System.out.println(grid[row][col]);
            }
        }
    }
}