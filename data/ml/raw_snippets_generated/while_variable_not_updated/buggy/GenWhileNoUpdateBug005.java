public class GenWhileNoUpdateBug005 {
    static void countdown(int attempts) {
        while (attempts > 0) {
            System.out.println("left: " + attempts);
        }
    }
}
