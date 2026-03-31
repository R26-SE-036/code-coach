package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix009 {
    public static void main(String[] args) {
        boolean ready = false;
        int tasks = 0;

        ready = tasks == 0;
        if (ready) {
            System.out.println("Nothing pending");
        }
    }
}