package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix003 {
    public static void main(String[] args) {
        boolean passed = false;
        int score = 50;

        passed = score >= 40;
        if (passed) {
            System.out.println("Pass");
        }
    }
}