public class GenWhileNoUpdateFix165 {
    static void pump(boolean valid, int level) {
        while (!valid) {
            System.out.println(level);
            level++;
            valid = level > 10;
        }
    }
}
