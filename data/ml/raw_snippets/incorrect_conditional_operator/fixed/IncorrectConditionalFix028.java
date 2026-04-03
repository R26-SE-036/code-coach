package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix028 {
    public void checkEvenSum(int a, int b) {
        boolean evenSum = (a + b) % 2 == 0;
        if (evenSum) {
            System.out.println("Even sum");
        }
    }
}
