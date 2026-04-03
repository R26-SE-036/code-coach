package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug027 {
    public void checkPrefix(String text) {
        boolean hasPrefix = false;
        if (hasPrefix = text.startsWith("https")) {
            System.out.println("Secure URL");
        }
    }
}
