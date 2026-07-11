public class GenWhileNoUpdateFix031 {
    static void pump(boolean verified, int count) {
        while (!verified) {
            System.out.println(count);
            count++;
            verified = count > 10;
        }
    }
}
