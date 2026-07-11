public class GenWhileNoUpdateBug031 {
    static void pump(boolean verified, int count) {
        while (!verified) {
            System.out.println(count);
            count++;
        }
    }
}
