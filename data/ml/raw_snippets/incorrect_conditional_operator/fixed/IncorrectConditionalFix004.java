package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix004 {
    public static void main(String[] args) {
        boolean passed = false;
        int score = 75;

        passed = score >= 50;
        if (passed) {
            System.out.println("Pass");
        }
    }
}