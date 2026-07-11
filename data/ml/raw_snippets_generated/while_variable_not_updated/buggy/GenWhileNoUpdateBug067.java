public class GenWhileNoUpdateBug067 {
    static void countdown(int total) {
        while (total > 0) {
            System.out.println("left: " + total);
        }
    }
}
