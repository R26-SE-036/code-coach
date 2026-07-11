public class GenWhileNoUpdateFix170 {
    static void pump(boolean active, int level) {
        while (!active) {
            System.out.println(level);
            level++;
            active = level > 10;
        }
    }
}
