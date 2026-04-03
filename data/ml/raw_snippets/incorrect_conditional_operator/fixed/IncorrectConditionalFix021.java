package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix021 {
    public void checkDivisibility(int n) {
        boolean divisible = n % 5 == 0;
        if (divisible) {
            System.out.println("Divisible by 5");
        }
    }
}
