package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix007 {
    public static void main(String[] args) {
        boolean valid = false;
        int age = 18;

        valid = age >= 18;
        if (valid) {
            System.out.println("Adult");
        }
    }
}