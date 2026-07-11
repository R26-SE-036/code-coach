public class GenWhileNoUpdateBug003 {
    static void countdown(int level) {
        while (level > 0) {
            System.out.println("left: " + level);
        }
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
