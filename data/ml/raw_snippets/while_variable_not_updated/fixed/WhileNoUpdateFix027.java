package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix027 {
    public static void main(String[] args) {
        for (int week = 1; week <= 2; week++) {
            int day = 1;
            while (day <= 5) {
                System.out.println("Week " + week + ", day " + day);
                day++;
            }
        }
    }
}
