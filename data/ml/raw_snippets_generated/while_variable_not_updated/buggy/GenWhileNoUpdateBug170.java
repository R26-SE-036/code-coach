public class GenWhileNoUpdateBug170 {
    static void pump(boolean active, int level) {
        while (!active) {
            System.out.println(level);
            level++;
        }
    }
}
