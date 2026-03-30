package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug006 {
    public static void main(String[] args) {
        boolean isEven = false;
        int number = 8;

        if (isEven = (number % 2 == 0)) {
            System.out.println("Even");
        }
    }
}