public class GenWhileNoUpdateFix152 {
    static void pump(boolean valid, int attempts) {
        while (!valid) {
            System.out.println(attempts);
            attempts++;
            valid = attempts > 10;
        }
    }
}
