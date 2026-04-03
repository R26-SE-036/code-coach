package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix022 {
    public void checkLength(String input) {
        boolean longEnough = input.length() >= 8;
        if (longEnough) {
            System.out.println("Valid length");
        }
    }
}
