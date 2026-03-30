package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug003 {
    public static void main(String[] args) {
        int score = 40;

        if (score = 50) {
            System.out.println("Pass");
        }
    }
}
