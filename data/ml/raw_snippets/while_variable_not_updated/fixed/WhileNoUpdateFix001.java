package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix001 {
    public static void main(String[] args) {
        int count = 1;
        while (count <= 5) {
            System.out.println("Count: " + count);
            count++;
        }
    }
}
