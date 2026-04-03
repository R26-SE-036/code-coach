package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug021 {
    public void checkDivisibility(int n) {
        boolean divisible = false;
        if (divisible = n % 5 == 0) {
            System.out.println("Divisible by 5");
        }
    }
}
