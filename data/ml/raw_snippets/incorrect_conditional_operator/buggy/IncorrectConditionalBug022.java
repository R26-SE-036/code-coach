package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug022 {
    public void checkLength(String input) {
        boolean longEnough = false;
        if (longEnough = input.length() >= 8) {
            System.out.println("Valid length");
        }
    }
}
