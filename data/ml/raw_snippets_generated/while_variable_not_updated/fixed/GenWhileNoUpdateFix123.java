public class GenWhileNoUpdateFix123 {
    static void pump(boolean active, int attempts) {
        while (!active) {
            System.out.println(attempts);
            attempts++;
            active = attempts > 10;
        }
    }
}
