package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug004 {
    public static void main(String[] args) {
        boolean passed = false;
        int score = 75;

        if (passed = score >= 50) {
            System.out.println("Pass");
        }
    }
}
