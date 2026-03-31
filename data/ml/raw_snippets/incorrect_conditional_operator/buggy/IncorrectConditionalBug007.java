package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug007 {
    public static void main(String[] args) {
        boolean valid = false;
        int age = 18;

        if (valid = age >= 18) {
            System.out.println("Adult");
        }
    }
}
