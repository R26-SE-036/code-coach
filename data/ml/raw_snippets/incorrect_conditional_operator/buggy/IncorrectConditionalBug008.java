package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug008 {
    public static void main(String[] args) {
        boolean matches = false;
        String code = "X123";

        if (matches = code.startsWith("X")) {
            System.out.println("Accepted");
        }
    }
}
