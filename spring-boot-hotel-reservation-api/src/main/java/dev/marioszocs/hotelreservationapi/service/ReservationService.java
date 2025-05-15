package dev.marioszocs.hotelreservationapi.service;

import dev.marioszocs.hotelreservationapi.dto.IdEntity;
import dev.marioszocs.hotelreservationapi.dto.SuccessEntity;
import dev.marioszocs.hotelreservationapi.entity.Reservation;

import java.util.List;

/**
 * Service interface for handling business logic related to reservations.
 */
public interface ReservationService {

    /**
     * Retrieves a list of all reservations.
     *
     * @return list of {@link Reservation} objects
     */
    List<Reservation> getAllReservations();

    /**
     * Retrieves a reservation by its ID.
     *
     * @param reservationId the ID of the reservation to retrieve
     * @return the {@link Reservation} object
     */
    Reservation getReservation(Integer reservationId);

    /**
     * Saves or updates the provided reservation.
     *
     * @param reservation the {@link Reservation} object to save
     * @return an {@link IdEntity} containing the ID of the saved reservation
     */
    IdEntity saveReservation(Reservation reservation);

    /**
     * Deletes the reservation with the given ID.
     *
     * @param reservationId the ID of the reservation to delete
     * @return a {@link SuccessEntity} indicating the outcome of the operation
     */
    SuccessEntity deleteReservation(Integer reservationId);

    /**
     * Checks if a hotel exists by the given ID.
     *
     * @param hotelId the ID of the hotel
     * @return true if the hotel exists, false otherwise
     */
    boolean validateHotelExistenceById(Integer hotelId);

    /**
     * Checks whether one date is before another.
     *
     * @param date1 the first date (in ISO format)
     * @param date2 the second date (in ISO format)
     * @return true if date1 is before date2, false otherwise
     */
    boolean dateIsBefore(String date1, String date2);

    /**
     * Determines if a new reservation overlaps with existing ones.
     *
     * @param reservation the reservation to check
     * @return true if overlapping, false otherwise
     */
    boolean reservationOverlaps(Reservation reservation);

    /**
     * Valid*
