package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug013 {
    public static void main(String[] args) {
        int row = 1;
        while (row <= 4) {
            String line = "";
            for (int col = 0; col < row; col++) {
                line += "*";
            }
            System.out.println(line);
        }
    }
}
