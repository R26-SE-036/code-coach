package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix002 {
    public static void main(String[] args) {
        int seconds = 10;
        while (seconds > 0) {
            System.out.println(seconds + "...");
            seconds--;
        }
        System.out.println("Lift off!");
    }
}
