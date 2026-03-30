package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix006 {
    public static void main(String[] args) {
        boolean isEven = false;
        int number = 8;

        isEven = (number % 2 == 0);
        if (isEven) {
            System.out.println("Even");
        }
    }
}
