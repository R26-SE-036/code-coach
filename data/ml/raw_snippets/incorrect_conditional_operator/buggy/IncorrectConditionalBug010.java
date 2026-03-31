package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug010 {
    public static void main(String[] args) {
        boolean same = false;
        int a = 5;
        int b = 5;

        if (same = a == b) {
            System.out.println("Equal");
        }
    }
}
