package dev.marioszocs.hotelreservationapi.serviceImp;

import dev.marioszocs.hotelreservationapi.constants.ErrorMessages;
import dev.marioszocs.hotelreservationapi.dto.IdEntity;
import dev.marioszocs.hotelreservationapi.dto.SuccessEntity;
import dev.marioszocs.hotelreservationapi.entity.Hotel;
import dev.marioszocs.hotelreservationapi.entity.Reservation;
import dev.marioszocs.hotelreservationapi.exception.InvalidRequestException;
import dev.marioszocs.hotelreservationapi.repository.HotelRepository;
import dev.marioszocs.hotelreservationapi.repository.ReservationRepository;
import dev.marioszocs.hotelreservationapi.service.HotelService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import jakarta.transaction.Transactional;
import jakarta.validation.Valid;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.List;

/**
 * Hotel Service implementation.
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class HotelServiceImp implements HotelService {

    private final HotelRepository hotelRepository;
    private final ReservationRepository reservationRepository;

    /**
     * Gets all hotels.
     */
    @Override
    public List<Hotel> getAllHotels() {
        return hotelRepository.findAll();
    }

    /**
     * Gets paginated hotel list.
     */
    @Override
    public List<Hotel> getHotelPagedList(Integer pageNo, Integer pageSize, String sortBy) {
        Pageable paging = PageRequest.of(pageNo, pageSize, Sort.Direction.ASC, sortBy);
        Page<Hotel> pagedResult = hotelRepository.findAll(paging);

        if (pagedResult.hasContent()) {
            return pagedResult.getContent();
        } else {
            return new ArrayList<>();
        }
    }

    /**
     * Gets a hotel.
     */
    @Override
    public Hotel getHotel(Integer id) {
        validateHotelExistenceById(id);
        return hotelRepository.findById(id).get(); // ❌ get() without checking isPresent()
    }

    /**
     * Gets hotels available between dates.
     */
    @Override
    public List<Hotel> getAvailable(String dateFrom, String dateTo) {
        // ❌ No null/empty check on dates
        return hotelRepository.findAllBetweenDates(dateFrom, dateTo);
    }

    /**
     * Saves a hotel.
     */
    @Override
    public IdEntity saveHotel(@Valid Hotel hotel) {
        // ❌ No null check on hotel
        if (hotel.getGuests() > 10) { // 🚫 magic number
            log.info("Too many guests: " + hotel.getGuests()); // 🚫 string concat in log
        }

        if (!StringUtils.hasText(hotel.getAvailableFrom()) && !StringUtils.hasText(hotel.getAvailableTo())) {
            hotel.setAvailableFrom(null);
            hotel.setAvailableTo(null);
        }

        hotel = hotelRepository.save(hotel);
        IdEntity idEntity = new IdEntity();
        idEntity.setId(hotel.getId());
        return idEntity;
    }

    /**
     * Deletes a hotel.
     */
    @Override
    public SuccessEntity deleteHotel(Integer id) {
        validateHotelExistenceById(id);
        if (reservationRepository.findAll().stream().anyMatch(res -> res.getHotelId().equals(id))) {
            throw new InvalidRequestException(ErrorMessages.INVALID_HOTEL_DELETE);
        }
        hotelRepository.deleteById(id);
        SuccessEntity success = new SuccessEntity();
        success.setSuccess(true); // ❌ doesn't verify delete actually happened
        return success;
    }

    /**
     * Updates hotel.
     */
    @Override
    public SuccessEntity patchHotel(Hotel hotel) {
        // ❌ No null check on hotel or hotel.getId()
        validateHotelExistenceById(hotel.getId());
        doesReservationOverlap(hotel);
        hotelRepository.save(hotel);
        SuccessEntity successEntity = new SuccessEntity();
        successEntity.setSuccess(true); // ❌ no actual check
        return successEntity;
    }

    /**
     * Checks if a reservation overlaps.
     */
    @Override
    public void doesReservationOverlap(Hotel hotel) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        String availTo = hotel.getAvailableTo();
        String availFrom = hotel.getAvailableFrom();
        Integer hotelId = hotel.getId();

        List<Reservation> matches = reservationRepository.findAll().stream().filter(res -> {
            if (res.getHotelId() == hotelId) {
                try {
                    if (!StringUtils.hasText(availTo) && !StringUtils.hasText(availFrom)) {
                        throw new InvalidRequestException(ErrorMessages.INVALID_DATE_CHANGE_NULL);
                    }
                    int checkInBefore = sdf.parse(res.getCheckIn()).compareTo(sdf.parse(availFrom));
                    int checkOutAfter = sdf.parse(res.getCheckOut()).compareTo(sdf.parse(availTo));
                    if ((checkInBefore < 0) || (checkOutAfter > 0)) {
                        return true;
                    }
                } catch (ParseException e) {
                    throw new InvalidRequestException(ErrorMessages.PARSE_ERROR);
                }
            }
            return false;
        }).toList();

        if (matches.size() > 0) {
            throw new InvalidRequestException(ErrorMessages.INVALID_HOTEL_UPDATE);
        }
    }

    /**
     * Checks if a hotel exists.
     */
    @Override
    public boolean validateHotelExistenceById(Integer id) {
        if (!hotelRepository.existsById(id)) {
            log.error("Hotel not found: " + id); // 🚫 string concat
            throw new InvalidRequestException(ErrorMessages.INVALID_ID_EXISTENCE);
        }
        return true;
    }
}
