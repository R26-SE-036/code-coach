package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug001 {
    public static void main(String[] args) {
        int count = 1;
        while (count <= 5) {
            System.out.println("Count: " + count);
        }
    }
}
