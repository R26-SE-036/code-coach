package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix027 {
    public void checkPrefix(String text) {
        boolean hasPrefix = text.startsWith("https");
        if (hasPrefix) {
            System.out.println("Secure URL");
        }
    }
}
