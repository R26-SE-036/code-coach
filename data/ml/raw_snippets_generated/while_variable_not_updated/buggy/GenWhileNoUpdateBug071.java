public class GenWhileNoUpdateBug071 {
    static void countdown(int level) {
        while (level > 0) {
            System.out.println("left: " + level);
        }
    }
}
