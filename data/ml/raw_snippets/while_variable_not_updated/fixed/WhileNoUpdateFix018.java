package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix018 {
    static void serveQueue(int waiting) {
        while (waiting > 0) {
            System.out.println("Serving customer, " + waiting + " left");
            waiting--;
        }
        System.out.println("Queue empty");
    }
}
