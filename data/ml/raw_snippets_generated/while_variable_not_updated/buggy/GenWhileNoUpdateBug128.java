public class GenWhileNoUpdateBug128 {
    static void countdown(int total) {
        while (total > 0) {
            System.out.println("left: " + total);
        }
    }
}
