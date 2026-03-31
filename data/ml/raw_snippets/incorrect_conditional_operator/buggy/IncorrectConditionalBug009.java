package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug009 {
    public static void main(String[] args) {
        boolean ready = false;
        int tasks = 0;

        if (ready = tasks == 0) {
            System.out.println("Nothing pending");
        }
    }
}
