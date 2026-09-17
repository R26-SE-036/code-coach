package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix016 {
    public static void main(String[] args) {
        int battery = 100;
        int hours = 0;
        while (battery > 20) {
            hours++;
            battery -= 15;
            System.out.println("Hour " + hours + ": " + battery + "%");
        }
    }
}
