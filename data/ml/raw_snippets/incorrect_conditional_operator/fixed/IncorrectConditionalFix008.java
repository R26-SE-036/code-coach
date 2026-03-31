package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix008 {
    public static void main(String[] args) {
        boolean matches = false;
        String code = "X123";

        matches = code.startsWith("X");
        if (matches) {
            System.out.println("Accepted");
        }
    }
}
