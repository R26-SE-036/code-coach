package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug003 {
    public static void main(String[] args) {
        boolean passed = false;
        int score = 50;

        if (passed = score >= 40) {
            System.out.println("Pass");
        }
    }
}