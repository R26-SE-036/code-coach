public class GenWhileNoUpdateFix077 {
    static void countdown(int level) {
        while (level > 0) {
            System.out.println("left: " + level);
            level--;
        }
    }
}
