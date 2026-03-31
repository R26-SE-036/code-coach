package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix010 {
    public static void main(String[] args) {
        boolean same = false;
        int a = 5;
        int b = 5;

        same = a == b;
        if (same) {
            System.out.println("Equal");
        }
    }
}
