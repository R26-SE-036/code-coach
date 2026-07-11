public class GenWhileNoUpdateBug061 {
    static void pump(boolean valid, int limit) {
        while (!valid) {
            System.out.println(limit);
            limit++;
        }
    }
}
