public class GenWhileNoUpdateBug092 {
    static void pump(boolean valid, int total) {
        while (!valid) {
            System.out.println(total);
            total++;
        }
    }
}
